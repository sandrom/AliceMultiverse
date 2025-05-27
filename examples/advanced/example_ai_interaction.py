"""Example of how an AI assistant would interact with Alice."""

from alicemultiverse.interface import AliceInterface, SearchRequest, TagRequest


def simulate_ai_conversation():
    """Simulate an AI assistant handling user requests through Alice."""

    # Initialize Alice
    alice = AliceInterface()

    print("=== AI ASSISTANT + ALICE INTERACTION EXAMPLE ===\n")

    # Scenario 1: User asks for recent cyberpunk images
    print("USER: Show me cyberpunk images from last week\n")

    print("AI THINKING: User wants cyberpunk images from last week.")
    print("AI: Let me search for those...\n")

    # AI translates to structured request
    search_request = SearchRequest(
        style_tags=["cyberpunk"], time_reference="last week", sort_by="created", limit=5
    )

    response = alice.search_assets(search_request)

    if response["success"]:
        print(f"AI: I found {len(response['data'])} cyberpunk images from last week:")
        for asset in response["data"]:
            print(f"   - {asset['filename']}")
            if asset["prompt"]:
                print(f"     Prompt: {asset['prompt']}")
            print(f"     Quality: {'★' * (asset['quality_stars'] or 0)}")
            print(f"     Tags: {', '.join(asset['tags'][:3])}")
    else:
        print(f"AI: Sorry, I couldn't search for images: {response['error']}")

    print("\n" + "-" * 50 + "\n")

    # Scenario 2: User wants to find hero shots
    print("USER: Find the hero shots we created for the music video\n")

    print("AI THINKING: User wants assets with 'hero' role for music video project.")
    print("AI: Searching for hero shots...\n")

    search_request = SearchRequest(
        roles=["hero"], description="music video", sort_by="quality", limit=3
    )

    response = alice.search_assets(search_request)

    if response["success"] and response["data"]:
        print("AI: Here are the hero shots from the music video project:")
        for asset in response["data"]:
            print(f"   - {asset['filename']} (Quality: {'★' * (asset['quality_stars'] or 0)})")
    else:
        print("AI: I couldn't find any hero shots. Would you like me to search differently?")

    print("\n" + "-" * 50 + "\n")

    # Scenario 3: User wants to organize and tag new content
    print(
        "USER: I just added new portraits to the inbox. Can you organize them and tag the best ones?\n"
    )

    print("AI THINKING: User wants to organize new files and tag high-quality ones.")
    print("AI: I'll organize the new files and identify the best portraits.\n")

    # First organize
    organize_response = alice.organize_media(
        {"enhanced_metadata": True, "quality_assessment": True}
    )

    if organize_response["success"]:
        print(f"AI: Organization complete! {organize_response['message']}")

        # Now find high-quality portraits
        search_request = SearchRequest(
            subject_tags=["portrait"], min_quality_stars=4, sort_by="created", limit=10
        )

        response = alice.search_assets(search_request)

        if response["success"] and response["data"]:
            # Tag the best ones
            best_assets = [asset["id"] for asset in response["data"][:3]]

            tag_request = TagRequest(
                asset_ids=best_assets, tags=["best-portrait", "selected"], tag_type="custom_tags"
            )

            tag_response = alice.tag_assets(tag_request)

            if tag_response["success"]:
                print(
                    f"\nAI: I've tagged the {tag_response['data']['tagged_count']} best portraits."
                )
                print("    Tagged assets:")
                for asset in response["data"][:3]:
                    print(f"    - {asset['filename']} (★ {asset['quality_stars']})")

    print("\n" + "-" * 50 + "\n")

    # Scenario 4: Finding similar assets
    print("USER: Find more images like this one (shows an image)\n")

    print("AI THINKING: User wants similar images. I need to identify the reference first.")
    print("AI: Let me find similar images...\n")

    # In reality, AI would get the asset_id from the user's selection
    # For demo, let's search for any asset first
    search_response = alice.search_assets(SearchRequest(limit=1))

    if search_response["success"] and search_response["data"]:
        reference_asset = search_response["data"][0]
        print(f"AI: Using '{reference_asset['filename']}' as reference...")

        similar_response = alice.find_similar_assets(reference_asset["id"], threshold=0.6)

        if similar_response["success"] and similar_response["data"]:
            print(f"\nAI: I found {len(similar_response['data'])} similar images:")
            for asset in similar_response["data"][:3]:
                print(f"   - {asset['filename']}")
                print(f"     Tags: {', '.join(asset['tags'][:3])}")

    print("\n" + "-" * 50 + "\n")

    # Show project context
    print("AI: Here's an overview of your project:\n")

    context_response = alice.get_project_context(
        {"include_stats": True, "include_recent_assets": True}
    )

    if context_response["success"]:
        context = context_response["data"]
        print(f"Total assets: {context['total_assets']}")
        print(f"Favorite styles: {', '.join(context['favorite_styles'])}")
        print(f"Assets by source: {context['assets_by_source']}")

        if "recent_assets" in context:
            print("\nRecent additions:")
            for asset in context["recent_assets"][:3]:
                print(f"   - {asset['filename']} ({asset['source']})")


def show_alice_capabilities():
    """Show what Alice can do for AI assistants."""

    print("\n=== ALICE CAPABILITIES FOR AI ASSISTANTS ===\n")

    print("1. SEARCH AND DISCOVERY:")
    print("   - Natural language: 'cyberpunk portraits from last week'")
    print("   - Structured search: by tags, quality, role, time")
    print("   - Find similar assets")
    print("   - Search by description")

    print("\n2. ORGANIZATION:")
    print("   - Process new media with rich metadata")
    print("   - Extract prompts and generation parameters")
    print("   - Automatic quality assessment")
    print("   - Detect relationships and variations")

    print("\n3. CREATIVE MANAGEMENT:")
    print("   - Tag assets with semantic labels")
    print("   - Set creative roles (hero, b-roll, reference)")
    print("   - Group related assets")
    print("   - Track project context")

    print("\n4. TECHNICAL ABSTRACTION:")
    print("   - AI never deals with file paths")
    print("   - No API key management")
    print("   - No infrastructure concerns")
    print("   - Alice handles all complexity")

    print("\n5. FUTURE CAPABILITIES (from spec):")
    print("   - Content generation through multiple providers")
    print("   - Multi-provider failover")
    print("   - Cost optimization")
    print("   - Music video synchronization")
    print("   - Workflow orchestration")


if __name__ == "__main__":
    # Note: This example assumes you have some test data organized
    # Run: alice --enhanced-metadata first to create some metadata

    print("Note: Run 'alice --enhanced-metadata' first to create some test data!\n")

    try:
        simulate_ai_conversation()
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure you have organized some files with --enhanced-metadata first!")

    print("\n" + "=" * 50 + "\n")

    show_alice_capabilities()
