"""
Example: AI Integration using REST API

This shows how AI assistants can integrate with Alice using the REST API
when MCP is not available or when building custom integrations.
"""

from typing import Any

import requests

# Base URL for Alice API
ALICE_API_URL = "http://localhost:8000"


class AliceAPIClient:
    """Client for interacting with Alice via REST API."""

    def __init__(self, base_url: str = ALICE_API_URL):
        self.base_url = base_url

    def search_assets(self, **kwargs) -> dict[str, Any]:
        """Search for assets using creative concepts."""
        response = requests.post(f"{self.base_url}/search", json=kwargs)
        return response.json()

    def organize_media(self, **kwargs) -> dict[str, Any]:
        """Organize and assess media files."""
        response = requests.post(f"{self.base_url}/organize", json=kwargs)
        return response.json()

    def tag_assets(self, asset_ids: list, **kwargs) -> dict[str, Any]:
        """Add semantic tags to assets."""
        response = requests.post(f"{self.base_url}/tag", json={"asset_ids": asset_ids, **kwargs})
        return response.json()

    def find_similar(self, asset_id: str, threshold: float = 0.8) -> dict[str, Any]:
        """Find similar assets."""
        response = requests.get(
            f"{self.base_url}/similar/{asset_id}", params={"threshold": threshold}
        )
        return response.json()

    def get_asset_info(self, asset_id: str) -> dict[str, Any]:
        """Get detailed asset information."""
        response = requests.get(f"{self.base_url}/asset/{asset_id}")
        return response.json()

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        response = requests.get(f"{self.base_url}/stats")
        return response.json()


def example_ai_workflow():
    """Example of how an AI assistant would use the REST API."""

    # Initialize client
    alice = AliceAPIClient()

    print("AI Assistant Workflow Example")
    print("=" * 50)

    # 1. Search for specific content
    print("\n1. Searching for cyberpunk portraits...")
    search_result = alice.search_assets(
        style_tags=["cyberpunk"], subject_tags=["portrait"], min_quality_stars=4, limit=5
    )

    if search_result["success"]:
        print(f"   Found {len(search_result['data']['assets'])} assets")
        for asset in search_result["data"]["assets"]:
            print(f"   - {asset['id']}: {asset.get('prompt', 'No prompt')}")

    # 2. Organize new media
    print("\n2. Organizing media files...")
    org_result = alice.organize_media(
        source_path="~/Downloads", quality_assessment=True, pipeline="standard"
    )

    if org_result["success"]:
        stats = org_result["data"]["stats"]
        print(f"   Organized {stats['organized']} files")
        print(f"   Quality distribution: {stats.get('by_quality', {})}")

    # 3. Tag assets for a project
    if search_result["success"] and search_result["data"]["assets"]:
        print("\n3. Tagging assets for project...")
        asset_ids = [a["id"] for a in search_result["data"]["assets"][:3]]

        tag_result = alice.tag_assets(
            asset_ids, style_tags=["hero-shot"], custom_tags=["cyberpunk-project-2024"], role="hero"
        )

        if tag_result["success"]:
            print(f"   Tagged {tag_result['data']['tagged_count']} assets")

    # 4. Find similar assets
    if search_result["success"] and search_result["data"]["assets"]:
        print("\n4. Finding similar assets...")
        reference_id = search_result["data"]["assets"][0]["id"]

        similar_result = alice.find_similar(reference_id, threshold=0.7)

        if similar_result["success"]:
            print(f"   Found {len(similar_result['data']['assets'])} similar assets")

    # 5. Get statistics
    print("\n5. Getting collection statistics...")
    stats_result = alice.get_stats()

    if stats_result["success"]:
        stats = stats_result["data"]
        print(f"   Total assets: {stats.get('total_assets', 0)}")
        print(f"   By source: {stats.get('by_source', {})}")


def example_custom_integration():
    """Example of building a custom AI assistant integration."""

    class CustomAIAssistant:
        def __init__(self):
            self.alice = AliceAPIClient()

        def handle_user_request(self, request: str) -> str:
            """Process user request and return formatted response."""

            # Example: User wants to create a mood board
            if "mood board" in request.lower():
                # Search for appropriate content
                results = self.alice.search_assets(
                    description=request, min_quality_stars=4, limit=20
                )

                if results["success"] and results["data"]["assets"]:
                    assets = results["data"]["assets"]
                    response = f"I found {len(assets)} high-quality images for your mood board:\n\n"

                    # Group by style
                    styles = {}
                    for asset in assets:
                        for tag in asset.get("tags", []):
                            if tag not in styles:
                                styles[tag] = []
                            styles[tag].append(asset)

                    for style, style_assets in list(styles.items())[:3]:
                        response += f"**{style.title()}** ({len(style_assets)} images)\n"

                    response += "\nWould you like me to create a collection with these images?"
                    return response
                else:
                    return "I couldn't find suitable images. Try being more specific about the mood or style."

            return "I can help you search, organize, and manage your creative assets. What would you like to do?"

    # Demo the custom assistant
    assistant = CustomAIAssistant()

    print("\n\nCustom AI Assistant Demo")
    print("=" * 50)

    user_request = "Create a dark atmospheric mood board for my horror game"
    print(f"\nUser: {user_request}")
    print(f"\nAssistant: {assistant.handle_user_request(user_request)}")


if __name__ == "__main__":
    # Note: Make sure the Alice MCP server is running first:
    # Configure Claude Desktop with the alice mcp-server

    try:
        # Test if API is available
        response = requests.get(ALICE_API_URL)

        # Run examples
        example_ai_workflow()
        example_custom_integration()

    except requests.ConnectionError:
        print("Error: Alice MCP server is not running.")
        print("Make sure the Alice MCP server is configured and running in Claude Desktop.")
        print("See README.md for setup instructions.")
