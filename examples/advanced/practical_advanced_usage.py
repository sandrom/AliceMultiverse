#!/usr/bin/env python3
"""
Practical Advanced Understanding Usage Example

This example shows how to integrate the advanced image understanding features
into real workflows, including:

1. Setting up a fashion photography project with custom instructions
2. Processing a batch of images with cost optimization
3. Using hierarchical tags for better organization
4. Monitoring costs and performance
"""

import asyncio
import logging
from pathlib import Path

from alicemultiverse.database.repository import AssetRepository
from alicemultiverse.understanding import (
    AdvancedBatchUnderstandingStage,
    AdvancedTagger,
    CustomInstructionManager,
    ImageUnderstandingStage,
    InstructionTemplate,
)

logger = logging.getLogger(__name__)


class AdvancedImageProcessor:
    """Example processor using advanced understanding features."""

    def __init__(self, project_id: str, repository: AssetRepository):
        """Initialize with project configuration.

        Args:
            project_id: The project identifier
            repository: Database repository for asset management
        """
        self.project_id = project_id
        self.repository = repository

        # Initialize advanced components
        self.instruction_manager = CustomInstructionManager()
        self.advanced_tagger = AdvancedTagger(repository)

        # Set up project-specific configuration
        self._setup_project_instructions()

    def _setup_project_instructions(self):
        """Set up custom instructions for the project."""
        # Example: Fashion photography project
        if "fashion" in self.project_id.lower():
            instructions = {
                "general": """
                Analyze this fashion image with focus on:
                1. Fashion elements: clothing, accessories, styling
                2. Model presentation: pose, expression, attitude
                3. Brand positioning: luxury vs. casual, target market
                4. Technical quality: lighting, composition, color grading
                5. Mood and aesthetic appeal
                """,
                "product": """
                For product shots, emphasize:
                - Product visibility and appeal
                - Styling context and lifestyle association
                - Commercial viability and target audience
                """
            }

            templates = ["fashion_detailed"]
            variables = {
                "additional_focus": "Luxury brand positioning and market appeal"
            }

            self.instruction_manager.set_project_instructions(
                self.project_id, instructions, templates, variables
            )
            logger.info(f"Set up fashion photography instructions for {self.project_id}")

        # Add more project types as needed
        elif "product" in self.project_id.lower():
            # Product photography setup
            instructions = {
                "general": "Focus on product features, quality, and commercial appeal"
            }
            templates = ["product_photography"]
            variables = {"product_category": "general", "target_platform": "e-commerce"}

            self.instruction_manager.set_project_instructions(
                self.project_id, instructions, templates, variables
            )

    async def process_single_image(self, image_path: Path,
                                 use_optimization: bool = True,
                                 budget_limit: float = None) -> dict:
        """Process a single image with advanced understanding.

        Args:
            image_path: Path to the image file
            use_optimization: Whether to use provider optimization
            budget_limit: Optional budget limit for this analysis

        Returns:
            Dictionary with analysis results and metadata
        """
        # Create advanced understanding stage
        stage = ImageUnderstandingStage(
            project_id=self.project_id,
            repository=self.repository,
            use_hierarchical_tags=True,
            use_custom_vocabulary=True,
            use_provider_optimization=use_optimization,
            budget_limit=budget_limit,
            detailed=False,
            generate_prompt=True,
            extract_tags=True
        )

        # Process the image
        metadata = {
            "media_type": "image",
            "project_id": self.project_id,
            "file_path": str(image_path)
        }

        result_metadata = stage.process(image_path, metadata)

        logger.info(f"Processed {image_path.name} - "
                   f"Tags: {len(result_metadata.get('all_tags', []))}, "
                   f"Cost: ${result_metadata.get('understanding_cost', 0):.4f}")

        return result_metadata

    async def process_batch(self, image_paths: list[Path],
                          max_concurrent: int = 5,
                          budget_limit: float = None,
                          show_progress: bool = True) -> list[dict]:
        """Process multiple images efficiently.

        Args:
            image_paths: List of image paths to process
            max_concurrent: Maximum concurrent analyses
            budget_limit: Total budget limit for the batch
            show_progress: Whether to show progress indicators

        Returns:
            List of metadata dictionaries
        """
        # Create advanced batch stage
        stage = AdvancedBatchUnderstandingStage(
            project_id=self.project_id,
            repository=self.repository,
            max_concurrent=max_concurrent,
            budget_limit=budget_limit,
            use_optimization=True,
            checkpoint_interval=10
        )

        # Prepare metadata list
        metadata_list = []
        for image_path in image_paths:
            metadata_list.append({
                "media_type": "image",
                "project_id": self.project_id,
                "file_path": str(image_path)
            })

        # Process batch
        if show_progress:
            print(f"Processing batch of {len(image_paths)} images...")

        result_metadata_list = await stage.process_batch(image_paths, metadata_list)

        # Calculate summary statistics
        total_cost = sum(m.get('understanding_cost', 0) for m in result_metadata_list)
        total_tags = sum(len(m.get('all_tags', [])) for m in result_metadata_list)

        logger.info(f"Batch complete: {len(image_paths)} images, "
                   f"${total_cost:.2f} total cost, {total_tags} total tags")

        return result_metadata_list

    def get_project_tag_summary(self) -> dict:
        """Get a summary of tags used in this project.

        Returns:
            Dictionary with tag statistics and common patterns
        """
        # Get project vocabulary to show custom tags
        vocab = self.advanced_tagger.get_project_vocabulary(self.project_id)
        all_tags = vocab.get_all_tags()

        summary = {
            "total_categories": len(all_tags),
            "total_tags": sum(len(tags) for tags in all_tags.values()),
            "categories": {}
        }

        for category, tags in all_tags.items():
            summary["categories"][category] = {
                "count": len(tags),
                "examples": list(tags)[:5]  # Show first 5 as examples
            }

        return summary

    def create_custom_template(self, template_id: str, name: str,
                             instructions: str, variables: dict = None):
        """Create a custom instruction template for this project type.

        Args:
            template_id: Unique identifier for the template
            name: Human-readable name
            instructions: The instruction text with variables
            variables: Dictionary of variable names and descriptions
        """
        template = InstructionTemplate(
            id=template_id,
            name=name,
            description=f"Custom template for {self.project_id}",
            instructions=instructions,
            variables=variables or {}
        )

        self.instruction_manager.create_template(template)
        logger.info(f"Created custom template: {template_id}")


async def example_fashion_photoshoot():
    """Example: Processing a fashion photoshoot with advanced features."""
    print("\n=== Fashion Photoshoot Example ===")

    # Initialize (in real usage, get repository from app config)
    repository = None  # AssetRepository() in production
    if not repository:
        print("Skipping database operations (no repository configured)")
        return

    project_id = "luxury_fashion_ss2024"
    processor = AdvancedImageProcessor(project_id, repository)

    # Example image paths (in real usage, these would be actual files)
    image_paths = [
        Path("fashion_shoot_001.jpg"),
        Path("fashion_shoot_002.jpg"),
        Path("fashion_shoot_003.jpg"),
        Path("fashion_shoot_004.jpg"),
        Path("fashion_shoot_005.jpg"),
    ]

    print(f"Processing {len(image_paths)} fashion images for project: {project_id}")

    # Process batch with cost control
    budget_limit = 2.0  # $2 budget for this batch

    try:
        results = await processor.process_batch(
            image_paths,
            max_concurrent=3,
            budget_limit=budget_limit,
            show_progress=True
        )

        # Analyze results
        print(f"\nResults: {len(results)} images processed")

        # Show tag summary
        tag_summary = processor.get_project_tag_summary()
        print(f"Tag categories: {tag_summary['total_categories']}")
        print(f"Total unique tags: {tag_summary['total_tags']}")

        # Show some example tags by category
        for category, info in list(tag_summary['categories'].items())[:3]:
            print(f"  {category}: {info['count']} tags - {', '.join(info['examples'])}")

    except Exception as e:
        print(f"Processing failed: {e}")


async def example_cost_optimized_processing():
    """Example: Cost-optimized processing with provider selection."""
    print("\n=== Cost-Optimized Processing Example ===")

    # This example shows how to process with strict cost controls
    project_id = "budget_conscious_project"

    # In a real application, you'd initialize this properly
    print("Setting up cost-optimized processing...")
    print("- Budget limit: $1.00")
    print("- Provider optimization: Enabled")
    print("- Batch processing: 10 images max")
    print("- Checkpoint saving: Every 5 images")

    # Mock processing results
    print("\nSimulated processing results:")
    print("✓ Selected cheapest provider: deepseek ($0.001/image)")
    print("✓ Processed 10 images within budget")
    print("✓ Total cost: $0.87 (under $1.00 limit)")
    print("✓ Average 12 tags per image")
    print("✓ All checkpoints saved successfully")


async def example_custom_instructions():
    """Example: Creating and using custom instructions."""
    print("\n=== Custom Instructions Example ===")

    instruction_manager = CustomInstructionManager()

    # Create a custom template for art analysis
    art_template = InstructionTemplate(
        id="art_gallery_analysis",
        name="Art Gallery Analysis",
        description="Analysis for art gallery and museum pieces",
        instructions="""
        Analyze this artwork with focus on:

        1. Artistic Elements:
           - Style and movement (impressionism, modern, contemporary, etc.)
           - Technique and medium
           - Color palette and composition

        2. Cultural Context:
           - Historical period indicators
           - Cultural references and symbolism
           - Social or political themes

        3. Technical Quality:
           - Condition and preservation
           - Photography quality for cataloging
           - Display suitability

        4. Market Information:
           - Estimated era: {time_period}
           - Collection type: {collection_type}

        Focus especially on: {focus_area}
        """,
        variables={
            "time_period": "Historical time period to focus on",
            "collection_type": "Type of collection (permanent, temporary, private)",
            "focus_area": "Specific aspect to emphasize in analysis"
        }
    )

    instruction_manager.create_template(art_template)
    print("✓ Created custom art gallery analysis template")

    # Set up project with custom instructions
    project_id = "museum_digitization_2024"

    project_instructions = {
        "general": "Focus on art historical significance and digital archival quality",
        "paintings": "Emphasize artistic technique and historical context",
        "sculptures": "Focus on three-dimensional form and material analysis"
    }

    instruction_manager.set_project_instructions(
        project_id,
        project_instructions,
        templates=["art_gallery_analysis"],
        variables={
            "time_period": "19th-20th century",
            "collection_type": "permanent",
            "focus_area": "historical significance and artistic technique"
        }
    )

    print(f"✓ Configured project: {project_id}")

    # Build complete instructions
    complete_instructions = instruction_manager.build_analysis_instructions(
        project_id, "paintings"
    )

    print(f"✓ Generated {len(complete_instructions)} character instruction set")
    print("Instructions include project settings + custom template + variables")


async def main():
    """Run all practical examples."""
    print("AliceMultiverse Advanced Understanding - Practical Examples")
    print("=" * 60)

    await example_fashion_photoshoot()
    await example_cost_optimized_processing()
    await example_custom_instructions()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("\nKey takeaways:")
    print("1. Advanced understanding scales from single images to large batches")
    print("2. Cost optimization prevents budget overruns")
    print("3. Custom instructions adapt analysis to specific domains")
    print("4. Hierarchical tags improve organization and searchability")
    print("5. All features integrate seamlessly with existing AliceMultiverse workflow")


if __name__ == "__main__":
    asyncio.run(main())
