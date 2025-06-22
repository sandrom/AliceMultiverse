"""Custom instruction management for project-specific image analysis."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


@dataclass
class InstructionTemplate:
    """Template for custom analysis instructions."""

    id: str
    name: str
    description: str
    instructions: str
    variables: dict[str, str] = field(default_factory=dict)  # Variable name -> description
    examples: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def render(self, **kwargs) -> str:
        """Render the instruction template with variables."""
        rendered = self.instructions

        # Replace variables
        for var_name, var_value in kwargs.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, str(var_value))

        # Check for missing variables
        import re
        remaining_vars = re.findall(r'\{(\w+)\}', rendered)
        if remaining_vars:
            logger.warning(f"Missing variables in template {self.name}: {remaining_vars}")

        return rendered


@dataclass
class ProjectInstructions:
    """Project-specific analysis instructions."""

    project_id: str
    instructions: dict[str, str] = field(default_factory=dict)  # category -> instruction
    templates: list[str] = field(default_factory=list)  # Template IDs
    variables: dict[str, Any] = field(default_factory=dict)  # Project-level variables
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class CustomInstructionManager:
    """Manages custom instructions for image analysis."""

    def __init__(self, db_path: Path | None = None):
        """Initialize the instruction manager.

        Args:
            db_path: Path to DuckDB database file (None for in-memory)
        """
        self.db_path = db_path or ":memory:"
        self.conn = duckdb.connect(str(self.db_path))
        self._initialize_database()
        self._load_default_templates()

    def _initialize_database(self):
        """Create database tables for instructions."""
        # Templates table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS instruction_templates (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                instructions TEXT NOT NULL,
                variables JSON,
                examples JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Project instructions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS project_instructions (
                project_id VARCHAR PRIMARY KEY,
                instructions JSON NOT NULL,
                templates JSON,
                variables JSON,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Instruction history table (for tracking changes)
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS instruction_history_seq;
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS instruction_history (
                id INTEGER PRIMARY KEY DEFAULT nextval('instruction_history_seq'),
                project_id VARCHAR NOT NULL,
                change_type VARCHAR NOT NULL,  -- 'create', 'update', 'delete'
                old_value JSON,
                new_value JSON,
                changed_by VARCHAR,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        logger.info("Initialized custom instruction database")

    def _load_default_templates(self):
        """Load default instruction templates."""
        default_templates = [
            InstructionTemplate(
                id="fashion_detailed",
                name="Fashion Photography Analysis",
                description="Detailed analysis for fashion and portrait photography",
                instructions="""Analyze this fashion/portrait image with special attention to:

1. Fashion and Styling:
   - Describe all clothing items, accessories, and styling choices
   - Note fabric types, textures, and patterns
   - Identify fashion style (casual, formal, streetwear, haute couture, etc.)

2. Model and Pose:
   - Describe the model's pose, expression, and body language
   - Note any distinctive features or characteristics
   - Analyze the mood and emotion conveyed

3. Photography Technique:
   - Camera angle and framing
   - Lighting setup and quality
   - Depth of field and focus
   - Color grading and post-processing style

4. Brand/Editorial Feel:
   - What type of brand or publication would use this image?
   - Target audience and market segment
   - Overall aesthetic and vibe

{additional_focus}""",
                variables={
                    "additional_focus": "Any specific aspect to focus on"
                },
                examples=[{
                    "input": {"additional_focus": "Focus on vintage styling elements"},
                    "output": "Added emphasis on retro fashion elements, period-appropriate styling"
                }]
            ),

            InstructionTemplate(
                id="product_photography",
                name="Product Photography Analysis",
                description="Analysis focused on product shots and commercial photography",
                instructions="""Analyze this product image for commercial use:

1. Product Presentation:
   - Main product and any secondary items
   - Product condition and quality visible
   - Key features highlighted
   - Scale and proportions

2. Styling and Props:
   - Background and surface choices
   - Supporting props and their purpose
   - Color coordination
   - Overall composition

3. Technical Quality:
   - Sharpness and detail reproduction
   - Color accuracy and consistency
   - Lighting evenness and shadows
   - Post-processing quality

4. Commercial Appeal:
   - Target market indicators
   - Lifestyle associations
   - Emotional triggers
   - Call-to-action potential

Category: {product_category}
Platform: {target_platform}""",
                variables={
                    "product_category": "Type of product (electronics, fashion, food, etc.)",
                    "target_platform": "Where the image will be used (e-commerce, social media, print)"
                }
            ),

            InstructionTemplate(
                id="artistic_style",
                name="Artistic Style Analysis",
                description="Deep analysis of artistic and stylistic elements",
                instructions="""Provide an artistic analysis of this image:

1. Visual Style:
   - Art movement influences (impressionism, surrealism, minimalism, etc.)
   - Technique and medium appearance
   - Stylistic choices and their effects

2. Composition and Design:
   - Rule of thirds, golden ratio, or other principles
   - Balance and visual weight
   - Leading lines and visual flow
   - Negative space usage

3. Color Theory:
   - Color palette and harmony
   - Emotional impact of colors
   - Contrast and saturation choices

4. Artistic Intent:
   - Apparent message or theme
   - Symbolism and metaphors
   - Emotional resonance
   - Cultural or historical references

Specific style focus: {style_focus}""",
                variables={
                    "style_focus": "Particular artistic style or movement to emphasize"
                }
            ),

            InstructionTemplate(
                id="content_moderation",
                name="Content Moderation Analysis",
                description="Check for content policy compliance",
                instructions="""Analyze this image for content moderation purposes:

1. Safety Check:
   - Any violence, gore, or disturbing content
   - Nudity or sexual content
   - Hate symbols or offensive imagery
   - Drug or alcohol references

2. Legal Compliance:
   - Visible logos or trademarks
   - Recognizable people (privacy concerns)
   - Copyright-protected elements
   - Age-appropriate content

3. Platform Suitability:
   - Social media friendliness
   - Professional use appropriateness
   - Family-friendly rating

4. Cultural Sensitivity:
   - Potentially offensive elements
   - Cultural appropriation concerns
   - Religious or political symbols

Platform guidelines: {platform_rules}
Audience: {target_audience}""",
                variables={
                    "platform_rules": "Specific platform content guidelines",
                    "target_audience": "Intended audience (general, youth, professional)"
                }
            ),

            InstructionTemplate(
                id="character_consistency",
                name="Character Consistency Check",
                description="Verify character appearance consistency across images",
                instructions="""Analyze this character image for consistency tracking:

1. Physical Characteristics:
   - Face shape and features
   - Hair color, style, and length
   - Eye color and shape
   - Skin tone and complexion
   - Body type and proportions

2. Distinguishing Features:
   - Scars, tattoos, or markings
   - Accessories (glasses, jewelry)
   - Unique characteristics

3. Clothing and Style:
   - Outfit description
   - Color schemes
   - Style consistency

4. Pose and Expression:
   - Facial expression
   - Body language
   - Mood conveyed

Character name: {character_name}
Reference notes: {reference_notes}""",
                variables={
                    "character_name": "Name of the character being tracked",
                    "reference_notes": "Any specific features to verify"
                }
            )
        ]

        # Insert default templates if they don't exist
        for template in default_templates:
            self._save_template(template, update_if_exists=False)

    def _save_template(self, template: InstructionTemplate, update_if_exists: bool = True):
        """Save a template to the database."""
        try:
            if update_if_exists:
                self.conn.execute("""
                    INSERT OR REPLACE INTO instruction_templates
                    (id, name, description, instructions, variables, examples, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [
                    template.id,
                    template.name,
                    template.description,
                    template.instructions,
                    json.dumps(template.variables),
                    json.dumps(template.examples),
                    datetime.now()
                ])
            else:
                # Only insert if doesn't exist
                existing = self.conn.execute(
                    "SELECT id FROM instruction_templates WHERE id = ?",
                    [template.id]
                ).fetchone()

                if not existing:
                    self.conn.execute("""
                        INSERT INTO instruction_templates
                        (id, name, description, instructions, variables, examples)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [
                        template.id,
                        template.name,
                        template.description,
                        template.instructions,
                        json.dumps(template.variables),
                        json.dumps(template.examples)
                    ])
        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")

    def create_template(self, template: InstructionTemplate) -> None:
        """Create a new instruction template."""
        self._save_template(template, update_if_exists=False)
        logger.info(f"Created instruction template: {template.name}")

    def get_template(self, template_id: str) -> InstructionTemplate | None:
        """Get a template by ID."""
        result = self.conn.execute(
            "SELECT * FROM instruction_templates WHERE id = ?",
            [template_id]
        ).fetchone()

        if result:
            return InstructionTemplate(
                id=result[0],
                name=result[1],
                description=result[2],
                instructions=result[3],
                variables=json.loads(result[4]) if result[4] else {},
                examples=json.loads(result[5]) if result[5] else [],
                created_at=result[6],
                updated_at=result[7]
            )
        return None

    def list_templates(self) -> list[InstructionTemplate]:
        """List all available templates."""
        results = self.conn.execute(
            "SELECT * FROM instruction_templates ORDER BY name"
        ).fetchall()

        templates = []
        for result in results:
            templates.append(InstructionTemplate(
                id=result[0],
                name=result[1],
                description=result[2],
                instructions=result[3],
                variables=json.loads(result[4]) if result[4] else {},
                examples=json.loads(result[5]) if result[5] else [],
                created_at=result[6],
                updated_at=result[7]
            ))

        return templates

    def set_project_instructions(self, project_id: str, instructions: dict[str, str],
                                templates: list[str] | None = None,
                                variables: dict[str, Any] | None = None) -> None:
        """Set custom instructions for a project.

        Args:
            project_id: The project ID
            instructions: Dictionary of category -> instruction text
            templates: List of template IDs to use
            variables: Project-level variables for templates
        """
        # Record history
        old_value = self.get_project_instructions(project_id)

        # Save new instructions
        self.conn.execute("""
            INSERT OR REPLACE INTO project_instructions
            (project_id, instructions, templates, variables, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, [
            project_id,
            json.dumps(instructions),
            json.dumps(templates or []),
            json.dumps(variables or {}),
            datetime.now()
        ])

        # Record in history
        self.conn.execute("""
            INSERT INTO instruction_history
            (project_id, change_type, old_value, new_value)
            VALUES (?, ?, ?, ?)
        """, [
            project_id,
            'update' if old_value else 'create',
            json.dumps(old_value.__dict__) if old_value else None,
            json.dumps({
                'instructions': instructions,
                'templates': templates or [],
                'variables': variables or {}
            })
        ])

        logger.info(f"Updated instructions for project {project_id}")

    def get_project_instructions(self, project_id: str) -> ProjectInstructions | None:
        """Get custom instructions for a project."""
        result = self.conn.execute(
            "SELECT * FROM project_instructions WHERE project_id = ? AND active = TRUE",
            [project_id]
        ).fetchone()

        if result:
            return ProjectInstructions(
                project_id=result[0],
                instructions=json.loads(result[1]) if result[1] else {},
                templates=json.loads(result[2]) if result[2] else [],
                variables=json.loads(result[3]) if result[3] else {},
                active=result[4],
                created_at=result[5],
                updated_at=result[6]
            )
        return None

    def build_analysis_instructions(self, project_id: str, category: str = "general",
                                   template_vars: dict[str, Any] | None = None) -> str:
        """Build complete analysis instructions for a project.

        Args:
            project_id: The project ID
            category: Instruction category (general, fashion, product, etc.)
            template_vars: Variables to pass to templates

        Returns:
            Complete instruction text
        """
        instructions = []

        # Get project instructions
        project_inst = self.get_project_instructions(project_id)

        if project_inst:
            # Add category-specific instructions
            if category in project_inst.instructions:
                instructions.append(project_inst.instructions[category])
            elif "general" in project_inst.instructions:
                instructions.append(project_inst.instructions["general"])

            # Merge variables
            all_vars = {}
            all_vars.update(project_inst.variables)
            if template_vars:
                all_vars.update(template_vars)

            # Apply templates
            for template_id in project_inst.templates:
                template = self.get_template(template_id)
                if template:
                    rendered = template.render(**all_vars)
                    instructions.append(f"\n{template.name}:\n{rendered}")

        # Default instruction if none found
        if not instructions:
            instructions.append(
                "Analyze this image comprehensively, including subject matter, "
                "style, mood, technical quality, and any notable features."
            )

        return "\n\n".join(instructions)

    def close(self):
        """Close the database connection."""
        self.conn.close()
