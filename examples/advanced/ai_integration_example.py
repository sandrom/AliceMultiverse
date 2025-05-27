"""
Example: How AI Assistants Interact with Alice

This example demonstrates the proper way for AI assistants to communicate with
Alice using structured function calls. The AI never sees file paths or technical
details - only creative concepts and asset IDs.
"""

import json

# In a real AI integration, these would be the available functions
# that the AI can call. The AI would have these function definitions
# in its system prompt or tool definitions.

ALICE_FUNCTIONS = {
    "search_assets": {
        "description": "Search for assets using creative concepts",
        "parameters": {
            "description": "Natural language description (e.g. 'dark moody portraits')",
            "style_tags": "List of style tags (e.g. ['cyberpunk', 'minimalist'])",
            "mood_tags": "List of mood tags (e.g. ['energetic', 'melancholic'])",
            "subject_tags": "List of subject tags (e.g. ['portrait', 'landscape'])",
            "time_reference": "Time reference (e.g. 'last week', 'yesterday')",
            "min_quality_stars": "Minimum quality rating (1-5)",
            "limit": "Maximum number of results",
        },
    },
    "organize_media": {
        "description": "Organize and analyze media files",
        "parameters": {
            "source_path": "Source directory (defaults to inbox)",
            "quality_assessment": "Enable quality scoring",
            "enhanced_metadata": "Extract rich metadata for AI navigation",
            "pipeline": "Quality pipeline mode ('basic', 'standard', 'premium')",
        },
    },
    "tag_assets": {
        "description": "Add semantic tags to assets",
        "parameters": {
            "asset_ids": "List of asset IDs to tag",
            "style_tags": "Style descriptors to add",
            "mood_tags": "Mood/emotion tags to add",
            "subject_tags": "Subject matter tags to add",
            "role": "Asset role ('hero', 'b_roll', 'reference', etc.)",
        },
    },
    "find_similar_assets": {
        "description": "Find assets similar to a reference",
        "parameters": {
            "asset_id": "Reference asset ID",
            "threshold": "Similarity threshold (0.0-1.0)",
        },
    },
    "get_asset_info": {
        "description": "Get detailed information about an asset",
        "parameters": {"asset_id": "Asset ID to get info for"},
    },
    "create_collection": {
        "description": "Group assets into a named collection",
        "parameters": {
            "name": "Collection name",
            "asset_ids": "List of asset IDs to include",
            "description": "Collection description",
        },
    },
}


class AIAssistantExample:
    """Example AI assistant that interacts with Alice."""

    def __init__(self):
        # In reality, this would connect to the actual Alice interface
        # For this example, we'll simulate responses
        pass

    def handle_user_request(self, user_message: str) -> str:
        """
        This simulates how an AI would process a user request and
        translate it into Alice function calls.
        """

        # Example 1: User asks for specific style of images
        if "cyberpunk portraits" in user_message.lower():
            return self._example_style_search()

        # Example 2: User wants to organize new downloads
        elif "organize" in user_message.lower() and "downloads" in user_message.lower():
            return self._example_organize_media()

        # Example 3: User wants to create a hero image collection
        elif "hero" in user_message.lower() and "collection" in user_message.lower():
            return self._example_create_hero_collection()

        # Example 4: Complex creative workflow
        elif "music video" in user_message.lower():
            return self._example_music_video_workflow()

        else:
            return "I can help you search, organize, and manage your AI-generated media. What would you like to do?"

    def _example_style_search(self) -> str:
        """Example 1: Search by style and subject."""

        # Step 1: AI translates user intent into function call
        function_call = {
            "function": "search_assets",
            "parameters": {
                "style_tags": ["cyberpunk", "neon"],
                "subject_tags": ["portrait", "character"],
                "min_quality_stars": 4,
                "limit": 20,
            },
        }

        # Step 2: Alice returns results (simulated)
        alice_response = {
            "success": True,
            "message": "Found 15 assets matching your criteria",
            "data": {
                "assets": [
                    {
                        "id": "a7f3b2c1d4e5",
                        "filename": "neon_portrait_001.png",
                        "prompt": "cyberpunk portrait with neon lighting",
                        "tags": ["cyberpunk", "neon", "portrait"],
                        "quality_stars": 5,
                        "created": "2024-03-15T10:30:00",
                    },
                    {
                        "id": "b8g4c3d2e6f7",
                        "filename": "cyber_character_002.png",
                        "prompt": "futuristic character in cyberpunk city",
                        "tags": ["cyberpunk", "character", "neon"],
                        "quality_stars": 4,
                        "created": "2024-03-14T15:45:00",
                    },
                    # ... more results
                ]
            },
        }

        # Step 3: AI formats response for user
        return """I found 15 cyberpunk portraits for you! Here are the top results:

1. **Neon Portrait** (★★★★★)
   - Created: March 15, 2024
   - ID: a7f3b2c1d4e5
   - Prompt: "cyberpunk portrait with neon lighting"

2. **Cyber Character** (★★★★☆)
   - Created: March 14, 2024  
   - ID: b8g4c3d2e6f7
   - Prompt: "futuristic character in cyberpunk city"

Would you like to see more results or refine your search?"""

    def _example_organize_media(self) -> str:
        """Example 2: Organize media with quality assessment."""

        # Step 1: AI calls organize function
        function_call = {
            "function": "organize_media",
            "parameters": {
                "source_path": "~/Downloads",
                "quality_assessment": True,
                "enhanced_metadata": True,
                "pipeline": "standard",  # BRISQUE + SightEngine
            },
        }

        # Step 2: Alice processes and returns results
        alice_response = {
            "success": True,
            "message": "Successfully organized 47 files",
            "data": {
                "stats": {
                    "total": 47,
                    "organized": 42,
                    "duplicates": 5,
                    "by_quality": {"5_star": 8, "4_star": 15, "3_star": 12, "2_star": 7},
                    "by_source": {"midjourney": 25, "flux": 12, "dalle3": 5},
                },
                "cost": 0.042,  # $0.042 for SightEngine API calls
            },
        }

        # Step 3: AI summarizes for user
        return """I've organized your downloads! Here's what I found:

📁 **Organization Complete**
- Total files processed: 47
- Successfully organized: 42
- Duplicates removed: 5

⭐ **Quality Distribution:**
- 5-star: 8 images (exceptional quality)
- 4-star: 15 images (great quality)
- 3-star: 12 images (good quality)
- 2-star: 7 images (fair quality)

🎨 **By Source:**
- Midjourney: 25 images
- Flux: 12 images
- DALL-E 3: 5 images

💰 Quality assessment cost: $0.04

Your best images are now in the 5-star folders, ready for your projects!"""

    def _example_create_hero_collection(self) -> str:
        """Example 3: Multi-step workflow to create a collection."""

        # Step 1: Search for high-quality hero shot candidates
        search_call = {
            "function": "search_assets",
            "parameters": {
                "description": "dramatic hero shots with strong composition",
                "min_quality_stars": 5,
                "limit": 10,
            },
        }

        # Simulated search results
        search_results = ["a7f3b2c1d4e5", "b8g4c3d2e6f7", "c9h5d4e3f8g9"]

        # Step 2: Tag them as hero shots
        tag_call = {
            "function": "tag_assets",
            "parameters": {
                "asset_ids": search_results,
                "style_tags": ["hero-shot", "dramatic"],
                "role": "hero",
            },
        }

        # Step 3: Create collection
        collection_call = {
            "function": "create_collection",
            "parameters": {
                "name": "Hero Shots - March 2024",
                "asset_ids": search_results,
                "description": "Curated hero shots for marketing materials",
            },
        }

        return """I've created your hero shot collection!

🎯 **Collection: "Hero Shots - March 2024"**
- Found 10 potential hero shots
- Selected the 3 best based on composition and impact
- Tagged them for easy future reference
- All images are 5-star quality

The collection is ready for your marketing materials. Would you like to:
- View the images in the collection
- Add more images to it
- Create variations of these hero shots"""

    def _example_music_video_workflow(self) -> str:
        """Example 4: Complex creative workflow for music video."""

        # This demonstrates how AI would orchestrate multiple
        # Alice functions for a complex creative task

        workflow_steps = [
            {
                "step": "Analyze song mood",
                "function": "search_assets",
                "parameters": {
                    "description": "dark atmospheric visuals",
                    "mood_tags": ["mysterious", "intense"],
                    "limit": 50,
                },
            },
            {
                "step": "Find hero shots",
                "function": "search_assets",
                "parameters": {"role": "hero", "min_quality_stars": 5, "limit": 10},
            },
            {
                "step": "Gather B-roll",
                "function": "search_assets",
                "parameters": {
                    "role": "b_roll",
                    "style_tags": ["atmospheric", "abstract"],
                    "limit": 30,
                },
            },
            {
                "step": "Create project collection",
                "function": "create_collection",
                "parameters": {
                    "name": "Dark Atmosphere Music Video",
                    "description": "Assets for 3-minute atmospheric track",
                },
            },
        ]

        return """I'll help you create a music video! Here's my plan:

🎬 **Music Video Creation Workflow**

1. **Mood Analysis** ✓
   - Found 45 dark atmospheric visuals
   - Identified key visual themes: shadows, fog, neon accents

2. **Hero Shots** ✓
   - Selected 8 powerful establishing shots
   - Each one could serve as a video chapter marker

3. **B-Roll Library** ✓
   - Gathered 30 atmospheric transition shots
   - Mix of abstract patterns and mood pieces

4. **Project Collection** ✓
   - Created "Dark Atmosphere Music Video" collection
   - Total assets: 83 perfectly matched visuals

📊 **Asset Breakdown:**
- Hero shots: 8 (5-star quality)
- Atmospheric B-roll: 30 (4-5 stars)
- Transition elements: 15 (4 stars)
- Abstract overlays: 30 (3-5 stars)

Next steps:
- Would you like me to organize these by tempo/energy level?
- Should I find similar assets for specific song sections?
- Do you need me to identify assets that work well together?"""


def demonstrate_ai_interaction():
    """Show various examples of AI-Alice interaction."""

    ai = AIAssistantExample()

    print("AI-Alice Integration Examples")
    print("=" * 60)
    print()

    # Example user requests
    user_requests = [
        "Show me cyberpunk portraits",
        "Organize my downloads folder with quality checks",
        "Create a collection of hero shots for my project",
        "I need to make a music video with dark atmospheric visuals",
    ]

    for i, request in enumerate(user_requests, 1):
        print(f"Example {i}")
        print(f"User: {request}")
        print()
        response = ai.handle_user_request(request)
        print(f"AI Assistant: {response}")
        print()
        print("-" * 60)
        print()


def show_function_calling_pattern():
    """Demonstrate the actual function calling pattern for AI integration."""

    print("Function Calling Pattern for AI Integration")
    print("=" * 60)
    print()

    print("1. AI receives user request:")
    print('   User: "Find me the best cyberpunk portraits from last week"')
    print()

    print("2. AI constructs function call:")
    function_call = {
        "function": "search_assets",
        "parameters": {
            "style_tags": ["cyberpunk"],
            "subject_tags": ["portrait"],
            "time_reference": "last week",
            "min_quality_stars": 4,
            "sort_by": "quality",
            "limit": 10,
        },
    }
    print("   " + json.dumps(function_call, indent=4).replace("\n", "\n   "))
    print()

    print("3. Alice processes and returns structured data:")
    alice_response = {
        "success": True,
        "message": "Found 8 assets",
        "data": {
            "assets": [
                {
                    "id": "unique_hash_here",
                    "prompt": "cyberpunk portrait with neon lighting",
                    "tags": ["cyberpunk", "portrait", "neon"],
                    "quality_stars": 5,
                    "created": "2024-03-18T14:30:00",
                }
            ]
        },
    }
    print("   " + json.dumps(alice_response, indent=4).replace("\n", "\n   "))
    print()

    print("4. AI formats response for user (no file paths!):")
    print('   "I found 8 cyberpunk portraits from last week. The highest')
    print("    rated one is a neon-lit portrait created on March 18th with")
    print('    a 5-star quality rating."')
    print()

    print("Key Points:")
    print("- AI never sees or mentions file paths")
    print("- All interactions use asset IDs and creative concepts")
    print("- Responses focus on creative attributes, not technical details")
    print("- Alice handles all file system operations internally")


if __name__ == "__main__":
    # Show examples of AI interaction
    demonstrate_ai_interaction()

    print("\n" * 2)

    # Show the function calling pattern
    show_function_calling_pattern()
