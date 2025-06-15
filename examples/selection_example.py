"""Example of using the selection tracking system in AliceMultiverse."""

import asyncio

from alicemultiverse.interface.alice_structured import AliceStructuredInterface
from alicemultiverse.interface.structured_models import (
    SelectionCreateRequest,
    SelectionItemRequest,
    SelectionPurpose,
    SelectionSearchRequest,
    SelectionStatus,
    SelectionUpdateRequest,
)


async def main():
    """Demonstrate selection tracking functionality."""

    # Initialize Alice interface
    alice = AliceStructuredInterface()

    # Example 1: Create a new selection for a portfolio project
    print("\n=== Creating Portfolio Selection ===")
    create_request = SelectionCreateRequest(
        project_id="my-portfolio-project",  # This should be an existing project
        name="Best of 2024",
        purpose=SelectionPurpose.PORTFOLIO,
        description="Curated selection of best work from 2024 for portfolio showcase",
        criteria={
            "min_quality": 4,
            "themes": ["cyberpunk", "nature", "abstract"],
            "exclude_wip": True
        },
        constraints={
            "max_items": 20,
            "balance_themes": True
        },
        tags=["portfolio", "2024", "showcase"],
        metadata={
            "target_audience": "potential clients",
            "presentation_order": "theme-based"
        }
    )

    response = alice.create_selection(create_request)
    if response["success"]:
        print(f"Created selection: {response['data']['name']} (ID: {response['data']['selection_id']})")
        selection_id = response["data"]["selection_id"]
    else:
        print(f"Failed to create selection: {response['error']}")
        return

    # Example 2: Add items to the selection
    print("\n=== Adding Items to Selection ===")

    # In a real scenario, you would get these from searching your assets
    items_to_add = [
        SelectionItemRequest(
            asset_hash="abc123def456...",  # Replace with real asset hashes
            file_path="/path/to/image1.png",
            selection_reason="Perfect example of cyberpunk aesthetic with neon colors",
            quality_notes="Sharp details, excellent composition",
            usage_notes="Use as hero image for cyberpunk section",
            tags=["cyberpunk", "hero"],
            role="hero",
            related_assets=["def789ghi012..."],  # Other similar assets
            custom_metadata={
                "client_feedback": "loved the color palette",
                "display_size": "large"
            }
        ),
        SelectionItemRequest(
            asset_hash="xyz789uvw012...",
            file_path="/path/to/image2.png",
            selection_reason="Beautiful nature scene with dramatic lighting",
            quality_notes="High resolution, vibrant colors",
            usage_notes="Supporting image for nature section",
            tags=["nature", "landscape"],
            role="supporting",
            alternatives=["uvw456rst789..."],  # Alternative options considered
        ),
    ]

    update_request = SelectionUpdateRequest(
        selection_id=selection_id,
        add_items=items_to_add,
        notes="Initial selection of hero and supporting images"
    )

    response = alice.update_selection(update_request)
    if response["success"]:
        print(f"Added {len(items_to_add)} items to selection")
        print(f"Total items now: {response['data']['item_count']}")
    else:
        print(f"Failed to add items: {response['error']}")

    # Example 3: Search for selections
    print("\n=== Searching for Portfolio Selections ===")
    search_request = SelectionSearchRequest(
        project_id="my-portfolio-project",
        purpose=SelectionPurpose.PORTFOLIO,
        status=SelectionStatus.DRAFT
    )

    response = alice.search_selections(search_request)
    if response["success"]:
        print(f"Found {response['data']['total_count']} portfolio selections:")
        for sel in response["data"]["selections"]:
            print(f"  - {sel['name']} ({sel['status']}) - {sel['item_count']} items")

    # Example 4: Update selection status
    print("\n=== Updating Selection Status ===")
    status_update = SelectionUpdateRequest(
        selection_id=selection_id,
        update_status=SelectionStatus.ACTIVE,
        notes="Finalized selection for client presentation"
    )

    response = alice.update_selection(status_update)
    if response["success"]:
        print(f"Selection status updated to: {response['data']['status']}")

    # Example 5: Get detailed selection information
    print("\n=== Getting Selection Details ===")
    response = alice.get_selection("my-portfolio-project", selection_id)
    if response["success"]:
        data = response["data"]
        print(f"Selection: {data['name']}")
        print(f"Purpose: {data['purpose']}")
        print(f"Status: {data['status']}")
        print(f"Items: {len(data['items'])}")
        print(f"Statistics: {data['statistics']}")

        if data['items']:
            print("\nFirst item details:")
            item = data['items'][0]
            print(f"  - Asset: {item['asset_hash'][:16]}...")
            print(f"  - Reason: {item['selection_reason']}")
            print(f"  - Role: {item['role']}")

    # Example 6: Export selection
    print("\n=== Exporting Selection ===")
    export_request = {
        "selection_id": selection_id,
        "export_path": "/path/to/export/portfolio_2024",
        "export_settings": {
            "include_metadata": True,
            "create_presentation": True,
            "image_format": "high_quality"
        }
    }

    # Note: Export would create files at the specified path
    print("Export functionality configured (not executed in example)")


def demonstrate_selection_workflow():
    """Show a complete creative workflow with selections."""

    print("\n=== Creative Workflow Example ===")
    print("""
    1. Project Creation Phase:
       - Create project for new campaign
       - Define creative direction and constraints
    
    2. Asset Discovery Phase:
       - Search for relevant assets using tags/criteria
       - Browse and evaluate options
    
    3. Selection Building Phase:
       - Create selection with specific purpose (e.g., "Client Presentation")
       - Add assets with detailed notes about why they were chosen
       - Group related assets together
       - Define sequence for presentation
    
    4. Review and Refinement Phase:
       - Share selection with team/client
       - Update based on feedback
       - Remove rejected options
       - Add alternatives
    
    5. Finalization Phase:
       - Mark selection as final
       - Export for delivery
       - Track usage and outcomes
    
    Benefits:
    - Complete history of creative decisions
    - Reusable selections for similar projects
    - Clear documentation of choices
    - Easy collaboration with notes and reasoning
    """)


if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())

    # Show workflow documentation
    demonstrate_selection_workflow()
