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


# TODO: Review unreachable code - @dataclass
# TODO: Review unreachable code - class ProjectInstructions:
# TODO: Review unreachable code - """Project-specific analysis instructions."""

# TODO: Review unreachable code - project_id: str
# TODO: Review unreachable code - instructions: dict[str, str] = field(default_factory=dict)  # category -> instruction
# TODO: Review unreachable code - templates: list[str] = field(default_factory=list)  # Template IDs
# TODO: Review unreachable code - variables: dict[str, Any] = field(default_factory=dict)  # Project-level variables
# TODO: Review unreachable code - active: bool = True
# TODO: Review unreachable code - created_at: datetime = field(default_factory=datetime.now)
# TODO: Review unreachable code - updated_at: datetime = field(default_factory=datetime.now)


# TODO: Review unreachable code - class CustomInstructionManager:
# TODO: Review unreachable code - """Manages custom instructions for image analysis."""

# TODO: Review unreachable code - def __init__(self, db_path: Path | None = None):
# TODO: Review unreachable code - """Initialize the instruction manager.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - db_path: Path to DuckDB database file (None for in-memory)
# TODO: Review unreachable code - """
# TODO: Review unreachable code - self.db_path = db_path or ":memory:"
# TODO: Review unreachable code - self.conn = duckdb.connect(str(self.db_path))
# TODO: Review unreachable code - self._initialize_database()
# TODO: Review unreachable code - self._load_default_templates()

# TODO: Review unreachable code - def _initialize_database(self):
# TODO: Review unreachable code - """Create database tables for instructions."""
# TODO: Review unreachable code - # Templates table
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - CREATE TABLE IF NOT EXISTS instruction_templates (
# TODO: Review unreachable code - id VARCHAR PRIMARY KEY,
# TODO: Review unreachable code - name VARCHAR NOT NULL,
# TODO: Review unreachable code - description TEXT,
# TODO: Review unreachable code - instructions TEXT NOT NULL,
# TODO: Review unreachable code - variables JSON,
# TODO: Review unreachable code - examples JSON,
# TODO: Review unreachable code - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
# TODO: Review unreachable code - updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# TODO: Review unreachable code - )
# TODO: Review unreachable code - """)

# TODO: Review unreachable code - # Project instructions table
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - CREATE TABLE IF NOT EXISTS project_instructions (
# TODO: Review unreachable code - project_id VARCHAR PRIMARY KEY,
# TODO: Review unreachable code - instructions JSON NOT NULL,
# TODO: Review unreachable code - templates JSON,
# TODO: Review unreachable code - variables JSON,
# TODO: Review unreachable code - active BOOLEAN DEFAULT TRUE,
# TODO: Review unreachable code - created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
# TODO: Review unreachable code - updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# TODO: Review unreachable code - )
# TODO: Review unreachable code - """)

# TODO: Review unreachable code - # Instruction history table (for tracking changes)
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - CREATE SEQUENCE IF NOT EXISTS instruction_history_seq;
# TODO: Review unreachable code - """)

# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - CREATE TABLE IF NOT EXISTS instruction_history (
# TODO: Review unreachable code - id INTEGER PRIMARY KEY DEFAULT nextval('instruction_history_seq'),
# TODO: Review unreachable code - project_id VARCHAR NOT NULL,
# TODO: Review unreachable code - change_type VARCHAR NOT NULL,  -- 'create', 'update', 'delete'
# TODO: Review unreachable code - old_value JSON,
# TODO: Review unreachable code - new_value JSON,
# TODO: Review unreachable code - changed_by VARCHAR,
# TODO: Review unreachable code - changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# TODO: Review unreachable code - )
# TODO: Review unreachable code - """)

# TODO: Review unreachable code - logger.info("Initialized custom instruction database")

# TODO: Review unreachable code - def _load_default_templates(self):
# TODO: Review unreachable code - """Load default instruction templates."""
# TODO: Review unreachable code - default_templates = [
# TODO: Review unreachable code - InstructionTemplate(
# TODO: Review unreachable code - id="fashion_detailed",
# TODO: Review unreachable code - name="Fashion Photography Analysis",
# TODO: Review unreachable code - description="Detailed analysis for fashion and portrait photography",
# TODO: Review unreachable code - instructions="""Analyze this fashion/portrait image with special attention to:

# TODO: Review unreachable code - 1. Fashion and Styling:
# TODO: Review unreachable code - - Describe all clothing items, accessories, and styling choices
# TODO: Review unreachable code - - Note fabric types, textures, and patterns
# TODO: Review unreachable code - - Identify fashion style (casual, formal, streetwear, haute couture, etc.)

# TODO: Review unreachable code - 2. Model and Pose:
# TODO: Review unreachable code - - Describe the model's pose, expression, and body language
# TODO: Review unreachable code - - Note any distinctive features or characteristics
# TODO: Review unreachable code - - Analyze the mood and emotion conveyed

# TODO: Review unreachable code - 3. Photography Technique:
# TODO: Review unreachable code - - Camera angle and framing
# TODO: Review unreachable code - - Lighting setup and quality
# TODO: Review unreachable code - - Depth of field and focus
# TODO: Review unreachable code - - Color grading and post-processing style

# TODO: Review unreachable code - 4. Brand/Editorial Feel:
# TODO: Review unreachable code - - What type of brand or publication would use this image?
# TODO: Review unreachable code - - Target audience and market segment
# TODO: Review unreachable code - - Overall aesthetic and vibe

# TODO: Review unreachable code - {additional_focus}""",
# TODO: Review unreachable code - variables={
# TODO: Review unreachable code - "additional_focus": "Any specific aspect to focus on"
# TODO: Review unreachable code - },
# TODO: Review unreachable code - examples=[{
# TODO: Review unreachable code - "input": {"additional_focus": "Focus on vintage styling elements"},
# TODO: Review unreachable code - "output": "Added emphasis on retro fashion elements, period-appropriate styling"
# TODO: Review unreachable code - }]
# TODO: Review unreachable code - ),

# TODO: Review unreachable code - InstructionTemplate(
# TODO: Review unreachable code - id="product_photography",
# TODO: Review unreachable code - name="Product Photography Analysis",
# TODO: Review unreachable code - description="Analysis focused on product shots and commercial photography",
# TODO: Review unreachable code - instructions="""Analyze this product image for commercial use:

# TODO: Review unreachable code - 1. Product Presentation:
# TODO: Review unreachable code - - Main product and any secondary items
# TODO: Review unreachable code - - Product condition and quality visible
# TODO: Review unreachable code - - Key features highlighted
# TODO: Review unreachable code - - Scale and proportions

# TODO: Review unreachable code - 2. Styling and Props:
# TODO: Review unreachable code - - Background and surface choices
# TODO: Review unreachable code - - Supporting props and their purpose
# TODO: Review unreachable code - - Color coordination
# TODO: Review unreachable code - - Overall composition

# TODO: Review unreachable code - 3. Technical Quality:
# TODO: Review unreachable code - - Sharpness and detail reproduction
# TODO: Review unreachable code - - Color accuracy and consistency
# TODO: Review unreachable code - - Lighting evenness and shadows
# TODO: Review unreachable code - - Post-processing quality

# TODO: Review unreachable code - 4. Commercial Appeal:
# TODO: Review unreachable code - - Target market indicators
# TODO: Review unreachable code - - Lifestyle associations
# TODO: Review unreachable code - - Emotional triggers
# TODO: Review unreachable code - - Call-to-action potential

# TODO: Review unreachable code - Category: {product_category}
# TODO: Review unreachable code - Platform: {target_platform}""",
# TODO: Review unreachable code - variables={
# TODO: Review unreachable code - "product_category": "Type of product (electronics, fashion, food, etc.)",
# TODO: Review unreachable code - "target_platform": "Where the image will be used (e-commerce, social media, print)"
# TODO: Review unreachable code - }
# TODO: Review unreachable code - ),

# TODO: Review unreachable code - InstructionTemplate(
# TODO: Review unreachable code - id="artistic_style",
# TODO: Review unreachable code - name="Artistic Style Analysis",
# TODO: Review unreachable code - description="Deep analysis of artistic and stylistic elements",
# TODO: Review unreachable code - instructions="""Provide an artistic analysis of this image:

# TODO: Review unreachable code - 1. Visual Style:
# TODO: Review unreachable code - - Art movement influences (impressionism, surrealism, minimalism, etc.)
# TODO: Review unreachable code - - Technique and medium appearance
# TODO: Review unreachable code - - Stylistic choices and their effects

# TODO: Review unreachable code - 2. Composition and Design:
# TODO: Review unreachable code - - Rule of thirds, golden ratio, or other principles
# TODO: Review unreachable code - - Balance and visual weight
# TODO: Review unreachable code - - Leading lines and visual flow
# TODO: Review unreachable code - - Negative space usage

# TODO: Review unreachable code - 3. Color Theory:
# TODO: Review unreachable code - - Color palette and harmony
# TODO: Review unreachable code - - Emotional impact of colors
# TODO: Review unreachable code - - Contrast and saturation choices

# TODO: Review unreachable code - 4. Artistic Intent:
# TODO: Review unreachable code - - Apparent message or theme
# TODO: Review unreachable code - - Symbolism and metaphors
# TODO: Review unreachable code - - Emotional resonance
# TODO: Review unreachable code - - Cultural or historical references

# TODO: Review unreachable code - Specific style focus: {style_focus}""",
# TODO: Review unreachable code - variables={
# TODO: Review unreachable code - "style_focus": "Particular artistic style or movement to emphasize"
# TODO: Review unreachable code - }
# TODO: Review unreachable code - ),

# TODO: Review unreachable code - InstructionTemplate(
# TODO: Review unreachable code - id="content_moderation",
# TODO: Review unreachable code - name="Content Moderation Analysis",
# TODO: Review unreachable code - description="Check for content policy compliance",
# TODO: Review unreachable code - instructions="""Analyze this image for content moderation purposes:

# TODO: Review unreachable code - 1. Safety Check:
# TODO: Review unreachable code - - Any violence, gore, or disturbing content
# TODO: Review unreachable code - - Nudity or sexual content
# TODO: Review unreachable code - - Hate symbols or offensive imagery
# TODO: Review unreachable code - - Drug or alcohol references

# TODO: Review unreachable code - 2. Legal Compliance:
# TODO: Review unreachable code - - Visible logos or trademarks
# TODO: Review unreachable code - - Recognizable people (privacy concerns)
# TODO: Review unreachable code - - Copyright-protected elements
# TODO: Review unreachable code - - Age-appropriate content

# TODO: Review unreachable code - 3. Platform Suitability:
# TODO: Review unreachable code - - Social media friendliness
# TODO: Review unreachable code - - Professional use appropriateness
# TODO: Review unreachable code - - Family-friendly rating

# TODO: Review unreachable code - 4. Cultural Sensitivity:
# TODO: Review unreachable code - - Potentially offensive elements
# TODO: Review unreachable code - - Cultural appropriation concerns
# TODO: Review unreachable code - - Religious or political symbols

# TODO: Review unreachable code - Platform guidelines: {platform_rules}
# TODO: Review unreachable code - Audience: {target_audience}""",
# TODO: Review unreachable code - variables={
# TODO: Review unreachable code - "platform_rules": "Specific platform content guidelines",
# TODO: Review unreachable code - "target_audience": "Intended audience (general, youth, professional)"
# TODO: Review unreachable code - }
# TODO: Review unreachable code - ),

# TODO: Review unreachable code - InstructionTemplate(
# TODO: Review unreachable code - id="character_consistency",
# TODO: Review unreachable code - name="Character Consistency Check",
# TODO: Review unreachable code - description="Verify character appearance consistency across images",
# TODO: Review unreachable code - instructions="""Analyze this character image for consistency tracking:

# TODO: Review unreachable code - 1. Physical Characteristics:
# TODO: Review unreachable code - - Face shape and features
# TODO: Review unreachable code - - Hair color, style, and length
# TODO: Review unreachable code - - Eye color and shape
# TODO: Review unreachable code - - Skin tone and complexion
# TODO: Review unreachable code - - Body type and proportions

# TODO: Review unreachable code - 2. Distinguishing Features:
# TODO: Review unreachable code - - Scars, tattoos, or markings
# TODO: Review unreachable code - - Accessories (glasses, jewelry)
# TODO: Review unreachable code - - Unique characteristics

# TODO: Review unreachable code - 3. Clothing and Style:
# TODO: Review unreachable code - - Outfit description
# TODO: Review unreachable code - - Color schemes
# TODO: Review unreachable code - - Style consistency

# TODO: Review unreachable code - 4. Pose and Expression:
# TODO: Review unreachable code - - Facial expression
# TODO: Review unreachable code - - Body language
# TODO: Review unreachable code - - Mood conveyed

# TODO: Review unreachable code - Character name: {character_name}
# TODO: Review unreachable code - Reference notes: {reference_notes}""",
# TODO: Review unreachable code - variables={
# TODO: Review unreachable code - "character_name": "Name of the character being tracked",
# TODO: Review unreachable code - "reference_notes": "Any specific features to verify"
# TODO: Review unreachable code - }
# TODO: Review unreachable code - )
# TODO: Review unreachable code - ]

# TODO: Review unreachable code - # Insert default templates if they don't exist
# TODO: Review unreachable code - for template in default_templates:
# TODO: Review unreachable code - self._save_template(template, update_if_exists=False)

# TODO: Review unreachable code - def _save_template(self, template: InstructionTemplate, update_if_exists: bool = True):
# TODO: Review unreachable code - """Save a template to the database."""
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - if update_if_exists:
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - INSERT OR REPLACE INTO instruction_templates
# TODO: Review unreachable code - (id, name, description, instructions, variables, examples, updated_at)
# TODO: Review unreachable code - VALUES (?, ?, ?, ?, ?, ?, ?)
# TODO: Review unreachable code - """, [
# TODO: Review unreachable code - template.id,
# TODO: Review unreachable code - template.name,
# TODO: Review unreachable code - template.description,
# TODO: Review unreachable code - template.instructions,
# TODO: Review unreachable code - json.dumps(template.variables),
# TODO: Review unreachable code - json.dumps(template.examples),
# TODO: Review unreachable code - datetime.now()
# TODO: Review unreachable code - ])
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - # Only insert if doesn't exist
# TODO: Review unreachable code - existing = self.conn.execute(
# TODO: Review unreachable code - "SELECT id FROM instruction_templates WHERE id = ?",
# TODO: Review unreachable code - [template.id]
# TODO: Review unreachable code - ).fetchone()

# TODO: Review unreachable code - if not existing:
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - INSERT INTO instruction_templates
# TODO: Review unreachable code - (id, name, description, instructions, variables, examples)
# TODO: Review unreachable code - VALUES (?, ?, ?, ?, ?, ?)
# TODO: Review unreachable code - """, [
# TODO: Review unreachable code - template.id,
# TODO: Review unreachable code - template.name,
# TODO: Review unreachable code - template.description,
# TODO: Review unreachable code - template.instructions,
# TODO: Review unreachable code - json.dumps(template.variables),
# TODO: Review unreachable code - json.dumps(template.examples)
# TODO: Review unreachable code - ])
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.error(f"Failed to save template {template.id}: {e}")

# TODO: Review unreachable code - def create_template(self, template: InstructionTemplate) -> None:
# TODO: Review unreachable code - """Create a new instruction template."""
# TODO: Review unreachable code - self._save_template(template, update_if_exists=False)
# TODO: Review unreachable code - logger.info(f"Created instruction template: {template.name}")

# TODO: Review unreachable code - def get_template(self, template_id: str) -> InstructionTemplate | None:
# TODO: Review unreachable code - """Get a template by ID."""
# TODO: Review unreachable code - result = self.conn.execute(
# TODO: Review unreachable code - "SELECT * FROM instruction_templates WHERE id = ?",
# TODO: Review unreachable code - [template_id]
# TODO: Review unreachable code - ).fetchone()

# TODO: Review unreachable code - if result:
# TODO: Review unreachable code - return InstructionTemplate(
# TODO: Review unreachable code - id=result[0],
# TODO: Review unreachable code - name=result[1],
# TODO: Review unreachable code - description=result[2],
# TODO: Review unreachable code - instructions=result[3],
# TODO: Review unreachable code - variables=json.loads(result[4]) if result[4] else {},
# TODO: Review unreachable code - examples=json.loads(result[5]) if result[5] else [],
# TODO: Review unreachable code - created_at=result[6],
# TODO: Review unreachable code - updated_at=result[7]
# TODO: Review unreachable code - )
# TODO: Review unreachable code - return None

# TODO: Review unreachable code - def list_templates(self) -> list[InstructionTemplate]:
# TODO: Review unreachable code - """List all available templates."""
# TODO: Review unreachable code - results = self.conn.execute(
# TODO: Review unreachable code - "SELECT * FROM instruction_templates ORDER BY name"
# TODO: Review unreachable code - ).fetchall()

# TODO: Review unreachable code - templates = []
# TODO: Review unreachable code - for result in results:
# TODO: Review unreachable code - templates.append(InstructionTemplate(
# TODO: Review unreachable code - id=result[0],
# TODO: Review unreachable code - name=result[1],
# TODO: Review unreachable code - description=result[2],
# TODO: Review unreachable code - instructions=result[3],
# TODO: Review unreachable code - variables=json.loads(result[4]) if result[4] else {},
# TODO: Review unreachable code - examples=json.loads(result[5]) if result[5] else [],
# TODO: Review unreachable code - created_at=result[6],
# TODO: Review unreachable code - updated_at=result[7]
# TODO: Review unreachable code - ))

# TODO: Review unreachable code - return templates

# TODO: Review unreachable code - def set_project_instructions(self, project_id: str, instructions: dict[str, str],
# TODO: Review unreachable code - templates: list[str] | None = None,
# TODO: Review unreachable code - variables: dict[str, Any] | None = None) -> None:
# TODO: Review unreachable code - """Set custom instructions for a project.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - project_id: The project ID
# TODO: Review unreachable code - instructions: Dictionary of category -> instruction text
# TODO: Review unreachable code - templates: List of template IDs to use
# TODO: Review unreachable code - variables: Project-level variables for templates
# TODO: Review unreachable code - """
# TODO: Review unreachable code - # Record history
# TODO: Review unreachable code - old_value = self.get_project_instructions(project_id)

# TODO: Review unreachable code - # Save new instructions
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - INSERT OR REPLACE INTO project_instructions
# TODO: Review unreachable code - (project_id, instructions, templates, variables, updated_at)
# TODO: Review unreachable code - VALUES (?, ?, ?, ?, ?)
# TODO: Review unreachable code - """, [
# TODO: Review unreachable code - project_id,
# TODO: Review unreachable code - json.dumps(instructions),
# TODO: Review unreachable code - json.dumps(templates or []),
# TODO: Review unreachable code - json.dumps(variables or {}),
# TODO: Review unreachable code - datetime.now()
# TODO: Review unreachable code - ])

# TODO: Review unreachable code - # Record in history
# TODO: Review unreachable code - self.conn.execute("""
# TODO: Review unreachable code - INSERT INTO instruction_history
# TODO: Review unreachable code - (project_id, change_type, old_value, new_value)
# TODO: Review unreachable code - VALUES (?, ?, ?, ?)
# TODO: Review unreachable code - """, [
# TODO: Review unreachable code - project_id,
# TODO: Review unreachable code - 'update' if old_value else 'create',
# TODO: Review unreachable code - json.dumps(old_value.__dict__) if old_value else None,
# TODO: Review unreachable code - json.dumps({
# TODO: Review unreachable code - 'instructions': instructions,
# TODO: Review unreachable code - 'templates': templates or [],
# TODO: Review unreachable code - 'variables': variables or {}
# TODO: Review unreachable code - })
# TODO: Review unreachable code - ])

# TODO: Review unreachable code - logger.info(f"Updated instructions for project {project_id}")

# TODO: Review unreachable code - def get_project_instructions(self, project_id: str) -> ProjectInstructions | None:
# TODO: Review unreachable code - """Get custom instructions for a project."""
# TODO: Review unreachable code - result = self.conn.execute(
# TODO: Review unreachable code - "SELECT * FROM project_instructions WHERE project_id = ? AND active = TRUE",
# TODO: Review unreachable code - [project_id]
# TODO: Review unreachable code - ).fetchone()

# TODO: Review unreachable code - if result:
# TODO: Review unreachable code - return ProjectInstructions(
# TODO: Review unreachable code - project_id=result[0],
# TODO: Review unreachable code - instructions=json.loads(result[1]) if result[1] else {},
# TODO: Review unreachable code - templates=json.loads(result[2]) if result[2] else [],
# TODO: Review unreachable code - variables=json.loads(result[3]) if result[3] else {},
# TODO: Review unreachable code - active=result[4],
# TODO: Review unreachable code - created_at=result[5],
# TODO: Review unreachable code - updated_at=result[6]
# TODO: Review unreachable code - )
# TODO: Review unreachable code - return None

# TODO: Review unreachable code - def build_analysis_instructions(self, project_id: str, category: str = "general",
# TODO: Review unreachable code - template_vars: dict[str, Any] | None = None) -> str:
# TODO: Review unreachable code - """Build complete analysis instructions for a project.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - project_id: The project ID
# TODO: Review unreachable code - category: Instruction category (general, fashion, product, etc.)
# TODO: Review unreachable code - template_vars: Variables to pass to templates

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Complete instruction text
# TODO: Review unreachable code - """
# TODO: Review unreachable code - instructions = []

# TODO: Review unreachable code - # Get project instructions
# TODO: Review unreachable code - project_inst = self.get_project_instructions(project_id)

# TODO: Review unreachable code - if project_inst:
# TODO: Review unreachable code - # Add category-specific instructions
# TODO: Review unreachable code - if category in project_inst.instructions:
# TODO: Review unreachable code - instructions.append(project_inst.instructions[category])
# TODO: Review unreachable code - elif "general" in project_inst.instructions:
# TODO: Review unreachable code - instructions.append(project_inst.instructions["general"])

# TODO: Review unreachable code - # Merge variables
# TODO: Review unreachable code - all_vars = {}
# TODO: Review unreachable code - all_vars.update(project_inst.variables)
# TODO: Review unreachable code - if template_vars:
# TODO: Review unreachable code - all_vars.update(template_vars)

# TODO: Review unreachable code - # Apply templates
# TODO: Review unreachable code - for template_id in project_inst.templates:
# TODO: Review unreachable code - template = self.get_template(template_id)
# TODO: Review unreachable code - if template:
# TODO: Review unreachable code - rendered = template.render(**all_vars)
# TODO: Review unreachable code - instructions.append(f"\n{template.name}:\n{rendered}")

# TODO: Review unreachable code - # Default instruction if none found
# TODO: Review unreachable code - if not instructions:
# TODO: Review unreachable code - instructions.append(
# TODO: Review unreachable code - "Analyze this image comprehensively, including subject matter, "
# TODO: Review unreachable code - "style, mood, technical quality, and any notable features."
# TODO: Review unreachable code - )

# TODO: Review unreachable code - return "\n\n".join(instructions)

# TODO: Review unreachable code - def close(self):
# TODO: Review unreachable code - """Close the database connection."""
# TODO: Review unreachable code - self.conn.close()
