#!/usr/bin/env python3
"""Demo of similarity search with selections.

This example shows how to:
1. Create a selection of images
2. Use perceptual hashing to find similar images
3. Add the most similar images to expand the selection
"""

import json
from pathlib import Path

from alicemultiverse.interface.alice_structured import AliceStructuredInterface
from alicemultiverse.interface.structured_models import (
    MediaType,
    SearchRequest,
    SelectionCreateRequest,
    SelectionPurpose,
    SelectionUpdateRequest,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}\n")


def main():
    """Run similarity search demo."""
    # Initialize Alice
    alice = AliceStructuredInterface()

    # Step 1: Create or find a project
    print_section("Step 1: Finding Project")

    projects = alice.project_service.list_projects()
    if projects:
        project = projects[0]
        print(f"Using existing project: {project['name']}")
    else:
        print("No projects found. Creating new project...")
        project = alice.project_service.create_project(
            name="similarity-demo",
            description="Demo project for similarity search"
        )
        print(f"Created project: {project['name']}")

    project_id = project['id']

    # Step 2: Search for initial images to select
    print_section("Step 2: Searching for Initial Images")

    # Search for cyberpunk style images as an example
    search_request = SearchRequest(
        tags=["cyberpunk", "neon"],
        media_type=MediaType.IMAGE,
        limit=10
    )

    search_result = alice.search(search_request)
    if not search_result.success or not search_result.data['results']:
        print("No images found with cyberpunk/neon tags. Searching for any images...")
        # Fallback to any images
        search_request = SearchRequest(
            media_type=MediaType.IMAGE,
            limit=10
        )
        search_result = alice.search(search_request)

    if not search_result.success or not search_result.data['results']:
        print("No images found in the system. Please organize some images first.")
        return

    initial_images = search_result.data['results']
    print(f"Found {len(initial_images)} initial images")

    # Step 3: Create a selection with these images
    print_section("Step 3: Creating Selection")

    selection_request = SelectionCreateRequest(
        project_id=project_id,
        name="Cyberpunk Style Collection",
        purpose=SelectionPurpose.CURATION,
        description="A curated collection of cyberpunk aesthetic images",
        criteria={
            "style": "cyberpunk",
            "mood": "futuristic",
            "colors": ["neon", "purple", "blue"]
        },
        tags=["cyberpunk", "neon", "futuristic"]
    )

    selection_result = alice.create_selection(selection_request)
    if not selection_result.success:
        print(f"Failed to create selection: {selection_result.error}")
        return

    selection_id = selection_result.data['selection_id']
    print(f"Created selection: {selection_result.data['name']} (ID: {selection_id})")

    # Step 4: Add initial images to selection
    print_section("Step 4: Adding Initial Images to Selection")

    items_to_add = []
    for img in initial_images[:5]:  # Add first 5 images
        items_to_add.append({
            "asset_hash": img['content_hash'],
            "file_path": img['file_path'],
            "selection_reason": "Initial cyberpunk style reference",
            "tags": ["reference", "seed"],
            "role": "seed"
        })

    update_request = SelectionUpdateRequest(
        project_id=project_id,
        selection_id=selection_id,
        action="add_items",
        items=items_to_add,
        notes="Adding initial seed images for similarity search"
    )

    update_result = alice.update_selection(update_request)
    if update_result.success:
        print(f"Added {len(items_to_add)} images to selection")
    else:
        print(f"Failed to add images: {update_result.error}")
        return

    # Step 5: Find similar images
    print_section("Step 5: Finding Similar Images")

    similar_result = alice.find_similar_to_selection(
        project_id=project_id,
        selection_id=selection_id,
        threshold=15,  # Moderate similarity threshold
        limit=20,      # Find up to 20 similar images
        exclude_existing=True
    )

    if not similar_result.success:
        print(f"Failed to find similar images: {similar_result.error}")
        return

    similar_images = similar_result.data['results']
    print(f"Found {len(similar_images)} similar images")

    # Display similarity results
    if similar_images:
        print("\nTop 10 Most Similar Images:")
        print("-" * 60)
        for i, result in enumerate(similar_images[:10], 1):
            asset = result['asset']
            similarity = result['similarity']
            print(f"\n{i}. {Path(asset['file_path']).name}")
            print(f"   Distance: {similarity['min_distance']} (lower is more similar)")
            print(f"   Score: {similarity['recommendation_score']:.2%}")
            print(f"   Similar to {similarity['similar_to_count']} selection items")
            if asset['tags']:
                print(f"   Tags: {', '.join(asset['tags'][:5])}")

    # Step 6: Add the most similar images to selection
    print_section("Step 6: Expanding Selection with Similar Images")

    # Add top 5 most similar images
    expansion_items = []
    for result in similar_images[:5]:
        asset = result['asset']
        similarity = result['similarity']
        expansion_items.append({
            "asset_hash": asset['content_hash'],
            "file_path": asset['file_path'],
            "selection_reason": f"Similar to seed images (score: {similarity['recommendation_score']:.2%})",
            "quality_notes": f"Distance: {similarity['min_distance']}",
            "tags": ["discovered", "similar"],
            "role": "expanded"
        })

    if expansion_items:
        expand_request = SelectionUpdateRequest(
            project_id=project_id,
            selection_id=selection_id,
            action="add_items",
            items=expansion_items,
            notes="Expanding selection with similar images found through perceptual hashing"
        )

        expand_result = alice.update_selection(expand_request)
        if expand_result.success:
            print(f"Successfully expanded selection with {len(expansion_items)} similar images")
        else:
            print(f"Failed to expand selection: {expand_result.error}")

    # Step 7: Get final selection statistics
    print_section("Step 7: Final Selection Statistics")

    final_selection = alice.get_selection(project_id, selection_id)
    if final_selection.success:
        stats = final_selection.data['statistics']
        print(f"Selection: {final_selection.data['name']}")
        print(f"Total items: {stats['item_count']}")
        print(f"Roles: {json.dumps(stats.get('role_distribution', {}), indent=2)}")
        print(f"Status: {final_selection.data['status']}")

        # Show selection path for reference
        if final_selection.data.get('items'):
            first_item = final_selection.data['items'][0]
            selection_path = Path(first_item['file_path']).parent.parent / "selected"
            print(f"\nSelection files would be exported to: {selection_path}")


if __name__ == "__main__":
    main()
